import os
from dotenv import load_dotenv
load_dotenv()

sid = os.getenv('TWILIO_ACCOUNT_SID')
token = os.getenv('TWILIO_AUTH_TOKEN')

from twilio.rest import Client
client = Client(sid, token)

whatsapp_sid = 'SMd625242cd9eb38d3c73d4b10960dd184'
sms_sid = 'SMf3d4e4f5dd7665eb8c1168cdc5494b2f'

print('=' * 40)
print('MESSAGE DELIVERY STATUS')
print('=' * 40)
print()

w_msg = client.messages(whatsapp_sid).fetch()
print('[WHATSAPP]')
print('  To:     ', w_msg.to)
print('  Status: ', w_msg.status)
print('  Date:   ', w_msg.date_sent)
print()

s_msg = client.messages(sms_sid).fetch()
print('[SMS]')
print('  To:     ', s_msg.to)
print('  Status: ', s_msg.status)
print('  Date:   ', s_msg.date_sent)
print()
print('=' * 40)
