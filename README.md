# shoonya_straddle

*NOTE: I am not responsible for the profit or loss you make it stock market . use this at your own risk*
<br /> check If you have all the packages installed , otherwise install the respective packages <br />
This repository contains the sample code for running straddle in with Finvasia shoonya Api <br />
I am using a method where once the Login fucntion is called , we can store the token and use it to start another session< By using the default method we can't do this <br />
When you run a two or more files simultaneously only the latest will be active others gets stopped<br />

The sell orders will be market orders and buy orders will be SL-LMT orders<br/>
How to Use:<br />
1.Download the repository, change the details in the config.py file as per your details<br />
2.The Login file,it is used to generate the token and store it.<br />
3.The testttt.py file is the file you need to run the straddle strategy<br />
The expiry is calculated automatically , so no need to enter the expiry manually, but please cross check<br />
4.This is just an example , do change as per your requirements <br />
5.Note: There might be slippages while doing it live  <br />
