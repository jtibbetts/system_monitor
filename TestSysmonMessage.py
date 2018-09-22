
from SysmonMessageModule import SysmonMessage
import config

sm = SysmonMessage(config.CLOSET_DIR, "testchannel-kinexis-com.json")
result, error_msg = sm.read_notify_cache()
print "Result: " + str(result)
print "Error: " + error_msg