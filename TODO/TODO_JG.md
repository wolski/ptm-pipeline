2) Wegen der PTM-pipeline
- ich denke es wäre sicher wichtig, dass egal von woher man kommt (LFQ-FP, FP-TMT, BGS, DIANN) sollte es vom Format her passen und möglich sein, dass die PTM-pipeline nicht bricht

3) Outputs PTM-pipeline
- momentan schreiben wir meiner Meinung nach „zuviel“ verschiedene „gleiche“ outputs. (Was ja ok ist fürs testing).. 
—> allerdings dann für die Services wäre es meiner Meinung nach wünschenswert, wenn man nur gewisse Schritte macht und nicht alles durchlaufen lassen muss. 

Konkret:
- Beispiel (non-model-organisms oder sogar Bakterien): Die „integration“ DPU oder DPA soll laufen, auch die N-to-C plots die dazugehören sowie die SeqLogo Analysis
—> bei Bakterien z.B macht PTM-SEA KinasLib MEA, KinaseLib-GSEA wenig Sinn!

- bei Services:
—> hat man evt. Das Total Proteome NICHT. Trotzdem könnte man SeqLogo und N-to-C machen wollen

- bei Services:
—> möchte man evt. Nicht DPU und auch noch DPA sondern nur eines von beidem.

