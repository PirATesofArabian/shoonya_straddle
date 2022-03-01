# shoonya_straddle

*NOTE: I am not responsible for the profit or loss you make it stock market . use this at your own risk*

This repository contains the sample code for running straddle in with Finvasia shoonya Api 
I am using a method where once the Login fucntion is called , we can store the token and use it to start another session< By using the default method we can't do this 
When you run a two or more files simultaneously only the latest will be active others gets stopped

How to Use:
1.Download the repository, change the details in the config.py file as per your details
2.The Login file,it is used to generate the token and store it.
3.The testttt.py file is the file you need to run the straddle strategy
The expiry is calculated automatically , so no need to enter the expiry manually, but please cross check by running the datesexp.py file
4.This is just an example , do change as per your requirements 
5.Note: There might be slippages while doing it live  
