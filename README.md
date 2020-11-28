Zestimate Tracker (a/k/a update-zestimate)
==========================================

Python based AWS Lambda function for checking the Zillow Zestimate of a 
given property value.

When triggered, this function pulls a CSV from a configured S3 location 
and the current Zillow Zestimate (including rental estimates) for a 
specified property. If the date of the last update to the Zestimate is 
newer than the last date in the file, a message is published to an 
SNS topic with the new value and the full Zestimate response is 
appended to the CSV.

Expected Environment Variables
------------------------------

+ zpid - Zillow property ID to track
+ zwsid - Bridge Interactive API Server Token (for server-to-server communication)
+ bucket_name - S3 bucket name to store Zestimate history
+ bucket_key - S3 object name to store Zestimate history
+ sns_topic_arn - SNS topic to publish when new updates available

Deployment
----------

The included [Makefile](./Makefile) will build a ZIP file which can be 
deployed to AWS Lambda. This ZIP file will include all dependencies 
(including Pandas, and therefore rather large).

Contributing
============

This project is governed by a [Code of Conduct](./CODE_OF_CONDUCT.md). By 
participating in this project you agree to abide by these terms.

License
=======

The [MIT License](LICENSE) applies.
