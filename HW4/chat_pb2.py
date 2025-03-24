# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: chat.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'chat.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\nchat.proto\"2\n\x0cLoginRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\"!\n\rLogoutRequest\x12\x10\n\x08username\x18\x01 \x01(\t\"\'\n\x13ListAccountsRequest\x12\x10\n\x08page_num\x18\x01 \x01(\x05\")\n\x14ListAccountsResponse\x12\x11\n\tusernames\x18\x01 \x03(\t\"J\n\x12SendMessageRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x11\n\trecipient\x18\x02 \x01(\t\x12\x0f\n\x07message\x18\x03 \x01(\t\"6\n\x13ReadMessagesRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\r\n\x05limit\x18\x02 \x01(\x05\"B\n\x14ReadMessagesResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x1a\n\x08messages\x18\x02 \x03(\x0b\x32\x08.Message\"6\n\x07Message\x12\n\n\x02id\x18\x01 \x01(\x05\x12\x0e\n\x06sender\x18\x02 \x01(\t\x12\x0f\n\x07message\x18\x03 \x01(\t\";\n\x14\x44\x65leteMessageRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x11\n\trecipient\x18\x02 \x01(\t\":\n\x14\x44\x65leteAccountRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\",\n\x18ListenForMessagesRequest\x12\x10\n\x08username\x18\x01 \x01(\t\"G\n\x17ReplicateMessageRequest\x12\x19\n\x07message\x18\x01 \x01(\x0b\x32\x08.Message\x12\x11\n\trecipient\x18\x02 \x01(\t\"+\n\x08Response\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t\"\x12\n\x10HeartbeatRequest\"H\n\x15LeaderElectionRequest\x12\x1c\n\x14requesting_server_id\x18\x01 \x01(\t\x12\x11\n\tleader_id\x18\x02 \x01(\t\"]\n\x0bMessageData\x12\n\n\x02id\x18\x01 \x01(\x05\x12\x0e\n\x06sender\x18\x02 \x01(\t\x12\x11\n\trecipient\x18\x03 \x01(\t\x12\x0f\n\x07message\x18\x04 \x01(\t\x12\x0e\n\x06status\x18\x05 \x01(\t\"3\n\x08UserData\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x15\n\rpassword_hash\x18\x02 \x01(\x0c\"*\n\x0fSyncDataRequest\x12\x17\n\x0freplica_address\x18\x01 \x01(\t\"w\n\x10SyncDataResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x19\n\x11replica_addresses\x18\x02 \x03(\t\x12\x1e\n\x08messages\x18\x03 \x03(\x0b\x32\x0c.MessageData\x12\x18\n\x05users\x18\x04 \x03(\x0b\x32\t.UserData2\xea\x04\n\x0b\x43hatService\x12!\n\x05Login\x12\r.LoginRequest\x1a\t.Response\x12#\n\x06Logout\x12\x0e.LogoutRequest\x1a\t.Response\x12;\n\x0cListAccounts\x12\x14.ListAccountsRequest\x1a\x15.ListAccountsResponse\x12-\n\x0bSendMessage\x12\x13.SendMessageRequest\x1a\t.Response\x12;\n\x0cReadMessages\x12\x14.ReadMessagesRequest\x1a\x15.ReadMessagesResponse\x12\x31\n\rDeleteMessage\x12\x15.DeleteMessageRequest\x1a\t.Response\x12\x31\n\rDeleteAccount\x12\x15.DeleteAccountRequest\x1a\t.Response\x12:\n\x11ListenForMessages\x12\x19.ListenForMessagesRequest\x1a\x08.Message0\x01\x12\x37\n\x10ReplicateMessage\x12\x18.ReplicateMessageRequest\x1a\t.Response\x12)\n\tHeartbeat\x12\x11.HeartbeatRequest\x1a\t.Response\x12\x33\n\x0eLeaderElection\x12\x16.LeaderElectionRequest\x1a\t.Response\x12/\n\x08SyncData\x12\x10.SyncDataRequest\x1a\x11.SyncDataResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'chat_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_LOGINREQUEST']._serialized_start=14
  _globals['_LOGINREQUEST']._serialized_end=64
  _globals['_LOGOUTREQUEST']._serialized_start=66
  _globals['_LOGOUTREQUEST']._serialized_end=99
  _globals['_LISTACCOUNTSREQUEST']._serialized_start=101
  _globals['_LISTACCOUNTSREQUEST']._serialized_end=140
  _globals['_LISTACCOUNTSRESPONSE']._serialized_start=142
  _globals['_LISTACCOUNTSRESPONSE']._serialized_end=183
  _globals['_SENDMESSAGEREQUEST']._serialized_start=185
  _globals['_SENDMESSAGEREQUEST']._serialized_end=259
  _globals['_READMESSAGESREQUEST']._serialized_start=261
  _globals['_READMESSAGESREQUEST']._serialized_end=315
  _globals['_READMESSAGESRESPONSE']._serialized_start=317
  _globals['_READMESSAGESRESPONSE']._serialized_end=383
  _globals['_MESSAGE']._serialized_start=385
  _globals['_MESSAGE']._serialized_end=439
  _globals['_DELETEMESSAGEREQUEST']._serialized_start=441
  _globals['_DELETEMESSAGEREQUEST']._serialized_end=500
  _globals['_DELETEACCOUNTREQUEST']._serialized_start=502
  _globals['_DELETEACCOUNTREQUEST']._serialized_end=560
  _globals['_LISTENFORMESSAGESREQUEST']._serialized_start=562
  _globals['_LISTENFORMESSAGESREQUEST']._serialized_end=606
  _globals['_REPLICATEMESSAGEREQUEST']._serialized_start=608
  _globals['_REPLICATEMESSAGEREQUEST']._serialized_end=679
  _globals['_RESPONSE']._serialized_start=681
  _globals['_RESPONSE']._serialized_end=724
  _globals['_HEARTBEATREQUEST']._serialized_start=726
  _globals['_HEARTBEATREQUEST']._serialized_end=744
  _globals['_LEADERELECTIONREQUEST']._serialized_start=746
  _globals['_LEADERELECTIONREQUEST']._serialized_end=818
  _globals['_MESSAGEDATA']._serialized_start=820
  _globals['_MESSAGEDATA']._serialized_end=913
  _globals['_USERDATA']._serialized_start=915
  _globals['_USERDATA']._serialized_end=966
  _globals['_SYNCDATAREQUEST']._serialized_start=968
  _globals['_SYNCDATAREQUEST']._serialized_end=1010
  _globals['_SYNCDATARESPONSE']._serialized_start=1012
  _globals['_SYNCDATARESPONSE']._serialized_end=1131
  _globals['_CHATSERVICE']._serialized_start=1134
  _globals['_CHATSERVICE']._serialized_end=1752
# @@protoc_insertion_point(module_scope)
