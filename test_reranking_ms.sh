curl -X "POST" \
  "http://0.0.0.0:8000/v1/ranking" \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "model": "NV-Rerank-QA-Mistral-4B",
  "query": {"text": "which way should i go?"},
  "passages": [
    {"text": "two roads diverged in a yellow wood, and sorry i could not travel both and be one traveler, long i stood and looked down one as far as i could to where it bent in the undergrowth;"},
    {"text": "then took the other, as just as fair, and having perhaps the better claim because it was grassy and wanted wear, though as for that the passing there had worn them really about the same,"},
    {"text": "and both that morning equally lay in leaves no step had trodden black. oh, i marked the first for another day! yet knowing how way leads on to way i doubted if i should ever come back."},
    {"text": "i shall be telling this with a sigh somewhere ages and ages hense: two roads diverged in a wood, and i, i took the one less traveled by, and that has made all the difference."}
  ],
  "truncate": "END"
}'