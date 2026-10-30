If[!StringQ[$ScriptInputString] || StringTrim[$ScriptInputString] === "",
  Print["ERROR: Expected base64-encoded XLSX workbook on standard input."];
  Exit[1]
  ];

workbookBytes = Quiet @ Check[ByteArray[StringTrim[$ScriptInputString]], $Failed];
If[workbookBytes === $Failed || Length[workbookBytes] == 0,
  Print["ERROR: Could not decode the workbook input."];
  Exit[1]
  ];

workbookSheets = Quiet @ Check[
   ImportByteArray[workbookBytes, "Data"],
   $Failed
   ];
If[!ListQ[workbookSheets] || workbookSheets === {} ||
   !MatrixQ[First[workbookSheets]],
  Print["ERROR: Wolfram Cloud could not import the XLSX workbook."];
  Exit[1]
  ];

responseTable = First[workbookSheets];
If[Length[responseTable] < 2 || Length[First[responseTable]] < 13,
  Print["ERROR: The first workbook sheet does not contain the expected 13 columns."];
  Exit[1]
  ];
responseRows = Rest[responseTable];

validValueQ[value_] := value =!= "" && value =!= Null &&
   !MatchQ[value, _Missing] &&
   !(StringQ[value] && StringTrim[value] === "");
columnValues[column_Integer] :=
  Select[responseRows[[All, column]], validValueQ];
countValues[values_List] := ReverseSort[Counts[values]];

pieGraphic[counts_Association, title_String] := Module[
   {keys, values, total, legends},
   keys = Keys[counts];
   values = Values[counts];
   total = Total[values];
   If[total == 0, Return[Style[title <> " (no responses)", 16]]];
   legends = MapThread[
     Row[{#1, " (", #2, ")"}] &,
     {keys, values}
     ];
   PieChart[
    N[values/total],
    ChartLegends -> Placed[legends, Right],
    ChartStyle -> "Pastel",
    LabelingFunction -> (
      Placed[Row[{NumberForm[100 #, {3, 1}], "%"}], "RadialCallout"] &
      ),
    PlotLabel -> Style[title, 16, Bold],
    ImageSize -> 520
    ]
   ];

barGraphic[counts_Association, title_String, limit_: 20] := Module[
   {topCounts, labels, values},
   topCounts = Take[counts, UpTo[limit]];
   labels = Keys[topCounts];
   values = Values[topCounts];
   If[values === {}, Return[Style[title <> " (no responses)", 16]]];
   BarChart[
    Reverse[values],
    ChartLabels -> Placed[Reverse[labels], Left],
    ChartStyle -> ColorData[97, "ColorList"][[1]],
    BarOrigin -> Left,
    GridLines -> Automatic,
    PlotLabel -> Style[title, 16, Bold],
    Frame -> True,
    ImageSize -> 760
    ]
   ];

scoreGraphic[values_List, title_String, frameLabel_String] := Module[
   {scores, counts, total},
   scores = Select[values, NumericQ[#] && 0 <= # <= 10 &];
   counts = countValues[Round /@ scores];
   total = Length[scores];
   If[total == 0, Return[Style[title <> " (no numeric responses)", 16]]];
   BarChart[
    Lookup[counts, Range[0, 10], 0],
    ChartLabels -> Placed[Range[0, 10], Below],
    ChartStyle -> Brown,
    GridLines -> Automatic,
    Frame -> True,
    FrameLabel -> {frameLabel, "Response counts"},
    PlotLabel -> Style[title, 16, Bold],
    ImageSize -> 650
    ]
   ];

wordCloudGraphic[values_List, title_String] := Module[
   {text, words, excluded},
   text = StringRiffle[Select[values, StringQ], " "];
   excluded = {"university", "uni", "jacobs", "constructor", "name"};
   words = Select[
     TextWords[text],
     !MemberQ[excluded, ToLowerCase[#]] &
     ];
   If[words === {}, Return[Style[title <> " (no words)", 16]]];
   WordCloud[
    words,
    Stopwords -> excluded,
    ColorFunction -> "LakeColors",
    PlotLabel -> Style[title, 16, Bold],
    ImageSize -> 760
    ]
   ];

statusValues = columnValues[2];
statusOtherTerms = {
   "parents", "retired", "(non-)", "postdoc", "foundation",
   "adjunct", "freelancer", "exchange", "/faculty"
   };
statusValues = statusValues /. value_String :>
    If[AnyTrue[statusOtherTerms,
      StringContainsQ[ToLowerCase[value], ToLowerCase[#]] &],
     "Other Response Options",
     value
     ];

alternativeValues = columnValues[12];
alternativeValues = alternativeValues /. value_String :> Module[
    {folded = ToLowerCase[value]},
    Which[
     StringContainsQ[folded, "iub"] ||
      (StringContainsQ[folded, "international"] &&
       StringContainsQ[folded, "university"] &&
       StringContainsQ[folded, "bremen"]),
     "International University Bremen",
     StringContainsQ[folded, "bremen institute of technology and science"],
     "Bremen Institute of Technology and Science",
     StringContainsQ[folded, "bit - bremen institute of technology"] ||
      StringContainsQ[folded, "bremen institute of technology"],
     "Bremen Institute of Technology",
     AnyTrue[
      {
       "i think the most healty thing",
       "so a name should embody the spirit of diversity that jacobs champions",
       "any name which is not clearly associated with a potential",
       "society/politics etc.",
       "none of the above represents what jacobs stands for",
       "different unique name",
       "some artificial name that vaguely sounds like latin"
       },
      StringContainsQ[folded, #] &
      ],
     "A Unique Name",
     AnyTrue[
      {
       "polytechnische hochschule bremen", "charles babbage university",
       "bell university bremen", "jacobs international university",
       "jacobs university is in itself a best name this university can have",
       "technique university bremen", "bremen technological university",
       "bremen university of science and technology", "slay university",
       "paradigm university", "options besides constructor",
       "wesser river university", "lucid dream university",
       "for whom the bell tolls", "except constructor univeristy",
       "schaffhausen institute of technology bremen", "bell university",
       "bell international university", "innovator", "constructive",
       "international global challenges university (igcu)", "none of them"
       },
      StringContainsQ[folded, #] &
      ],
     "Other Response Options",
     True,
     value
     ]
    ];

charts = {
   pieGraphic[countValues[statusValues], "Q1 - Current status at the University"],
   barGraphic[countValues[columnValues[3]], "Q2 - Field of study, research, or work"],
   pieGraphic[countValues[columnValues[4]], "Q3 - Heard about renaming plans"],
   pieGraphic[countValues[columnValues[5]], "Q4 - Attended the Town Hall meeting"],
   pieGraphic[countValues[columnValues[6]], "Q5 - Keep the current University name"],
   scoreGraphic[
    columnValues[7],
    "Q6 - Association with Jacobs University Bremen",
    "0 = no association; 10 = very strong association"
    ],
   wordCloudGraphic[
    columnValues[8],
    "Q7 - Associations with Jacobs University Bremen"
    ],
   wordCloudGraphic[
    columnValues[9],
    "Q8 - Associations with Constructor University"
    ],
   scoreGraphic[
    columnValues[10],
    "Q9 - Feeling about renaming to Constructor University",
    "0 = dislike a lot; 10 = like a lot"
    ],
   pieGraphic[
    countValues[columnValues[11]],
    "Q10 - Study or work at Constructor University"
    ],
   barGraphic[
    countValues[alternativeValues],
    "Q11 - Suggested future name (top 20)"
    ],
   wordCloudGraphic[columnValues[13], "Q12 - Suggestions and ideas"]
   };

If[Length[charts] != 12,
  Print["ERROR: Expected 12 survey charts."];
  Exit[1]
  ];

charts
