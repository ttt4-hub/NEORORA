# NEORORA

## Run in the existing project
Stop Streamlit with Ctrl+C. Back up the old phase3_app outside the project. Replace only phase3_app with this folder. Run START_WINDOWS.bat, or install requirements.txt and run `streamlit run app.py` from this folder. Leave the existing phase1_data, phase2_model and .git folders unchanged.

## Included files
- Existing de-identified features and metadata for 209 patients.
- The supplied predictions.csv for 42 held-out test patients.
- The supplied model.joblib (23 inputs, 15 selected features, linear SVM, threshold 0.67).
- The supplied final_test_metrics.csv, baseline_vs_final.csv and evaluation figures.

Model inference dependencies include scikit-learn 1.7.2, matching the saved estimator, and joblib. Only the trusted team model bundled here is loaded. No serialized models can be uploaded through the interface.

## Senior
Consent -> upload one person's CSV -> validation and cleaning -> feature extraction -> model inference -> plain-language screening summary.
Columns: patient_id (or patient), date, text. Include original local posting times in YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS format. Dates without times receive a receipt and a request for the actual times, rather than inventing a night-posting feature. At least five distinct usable posts are required. Fewer than ten original posts do not support a reliable early/late comparison; change inputs follow the notebook convention of zero and the UI suppresses the comparison.

Each successfully analysed submission receives a new coded ID and appears in Clinician during that session. Raw text stays server-side in session memory. Only aggregates and the assessment are sent to the browser. Uploads are not written to disk or the historical patient data. Sessions are not durable patient accounts; there is no authentication or access-control system in this prototype.

## Clinician
Select a patient to review the available score, binary model classification, three exported explanations, recorded information, writing changes and expandable measurements. Only the 42 supplied test patients have precomputed assessments. Other historical patients retain their features and are not silently assigned new predictions. A new Senior submission is available in the same Streamlit session. One assessment is not presented as a longitudinal risk timeline.

## Researcher
Metrics are read from the supplied final_test_metrics.csv. Accuracy is 61.9%, ROC AUC is .650, precision is 79.2%, balanced accuracy is 60.8%. The figures are copied directly from the supplied evaluation files. These values describe 42 held-out patients, not all 209 patients. Feature importance describes the model overall, not an individual causal explanation.

## Model interpretation
Class 0 = Normal; class 1 = MCI/Dementia. Low is below .50, Medium is .50 to below .67, High is .67 and above. Bands are defined by the team model and do not represent validated disease severity. Scores are not established clinical disease probabilities. A low score does not rule out impairment. No alerts are sent to relatives automatically.

## Preprocessing provenance
post_processing.py adapts the reviewed normalization/anonymization and feature extraction cells from 02_nlp_anonymize.ipynb and 03_features_export.ipynb into pure functions. It retains their copied-content, diagnosis-term exclusion, vocabulary, sentence, behavioral and early/late feature rules. Input CSVs already supply the person's own post text and resolved dates/times; the original raw scraping-column selection is not applicable to this upload schema. Automated masking is imperfect and may leave identifying text. The uploaded ID is replaced with a generated code before processing. No model retraining is performed.

04_text_score.ipynb adds a possible text feature, but the supplied final model expects the original 23 features. This interface follows the supplied model bundle and does not invent a new model or substitute the experimental text-feature variant.

## Verification
All 42 saved risk scores and levels reproduce exactly from the provided saved estimator and the existing test features in the local verification environment. Tested a new 12-post upload through cleaning, extraction of all required inputs, and inference. Tested valid/invalid inputs, missing times, five-post edge case, duplicate submissions, measurement availability, selected patient state, evaluation metrics and interface element references. Visual browser rendering could not be verified here.

## Credits
Interface and integration prepared with ChatGPT/Codex. Dataset preparation, feature design, training and evaluation are the team's supplied work. The original notebooks and model are unchanged.
