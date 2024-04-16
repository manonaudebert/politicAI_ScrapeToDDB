## Lambda  ##
This is the lambda code which scrape the campaign promises & their status and push them to DDB. This is for the CBS AI Hackathon. 


## Upload a new version to Lambda
Run the following commands to delete the old zipped version & re-zip.
Need to move dependencies out of dependency folder first -temporarily moved there to keep package clean. 
```
rm lambdaFunc.zip
zip -r lambdaFunc.zip .
```

Upload zipped file. If the file is too big, need to upload it to S3 first. The lambda name is get_article_topics
