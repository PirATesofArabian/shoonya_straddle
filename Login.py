from NorenApi import NorenApi
import config
shoonya=NorenApi()

shoonya.login(config.username,config.pwd,config.factor2,config.vc,config.app_key,config.imei)