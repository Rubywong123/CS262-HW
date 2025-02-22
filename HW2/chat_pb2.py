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




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\nchat.proto\"2\n\x0cLoginRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\"\'\n\x13ListAccountsRequest\x12\x10\n\x08page_num\x18\x01 \x01(\x05\")\n\x14ListAccountsResponse\x12\x11\n\tusernames\x18\x01 \x03(\t\"J\n\x12SendMessageRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x11\n\trecipient\x18\x02 \x01(\t\x12\x0f\n\x07message\x18\x03 \x01(\t\"6\n\x13ReadMessagesRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\r\n\x05limit\x18\x02 \x01(\x05\"B\n\x14ReadMessagesResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x1a\n\x08messages\x18\x02 \x03(\x0b\x32\x08.Message\"6\n\x07Message\x12\n\n\x02id\x18\x01 \x01(\x05\x12\x0e\n\x06sender\x18\x02 \x01(\t\x12\x0f\n\x07message\x18\x03 \x01(\t\"O\n\x14\x44\x65leteMessageRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x11\n\trecipient\x18\x02 \x01(\t\x12\x12\n\nmessage_id\x18\x03 \x01(\x05\":\n\x14\x44\x65leteAccountRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\",\n\x18ListenForMessagesRequest\x12\x10\n\x08username\x18\x01 \x01(\t\"+\n\x08Response\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t2\xfb\x02\n\x0b\x43hatService\x12!\n\x05Login\x12\r.LoginRequest\x1a\t.Response\x12;\n\x0cListAccounts\x12\x14.ListAccountsRequest\x1a\x15.ListAccountsResponse\x12-\n\x0bSendMessage\x12\x13.SendMessageRequest\x1a\t.Response\x12;\n\x0cReadMessages\x12\x14.ReadMessagesRequest\x1a\x15.ReadMessagesResponse\x12\x31\n\rDeleteMessage\x12\x15.DeleteMessageRequest\x1a\t.Response\x12\x31\n\rDeleteAccount\x12\x15.DeleteAccountRequest\x1a\t.Response\x12:\n\x11ListenForMessages\x12\x19.ListenForMessagesRequest\x1a\x08.Message0\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'chat_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_LOGINREQUEST']._serialized_start=14
  _globals['_LOGINREQUEST']._serialized_end=64
  _globals['_LISTACCOUNTSREQUEST']._serialized_start=66
  _globals['_LISTACCOUNTSREQUEST']._serialized_end=105
  _globals['_LISTACCOUNTSRESPONSE']._serialized_start=107
  _globals['_LISTACCOUNTSRESPONSE']._serialized_end=148
  _globals['_SENDMESSAGEREQUEST']._serialized_start=150
  _globals['_SENDMESSAGEREQUEST']._serialized_end=224
  _globals['_READMESSAGESREQUEST']._serialized_start=226
  _globals['_READMESSAGESREQUEST']._serialized_end=280
  _globals['_READMESSAGESRESPONSE']._serialized_start=282
  _globals['_READMESSAGESRESPONSE']._serialized_end=348
  _globals['_MESSAGE']._serialized_start=350
  _globals['_MESSAGE']._serialized_end=404
  _globals['_DELETEMESSAGEREQUEST']._serialized_start=406
  _globals['_DELETEMESSAGEREQUEST']._serialized_end=485
  _globals['_DELETEACCOUNTREQUEST']._serialized_start=487
  _globals['_DELETEACCOUNTREQUEST']._serialized_end=545
  _globals['_LISTENFORMESSAGESREQUEST']._serialized_start=547
  _globals['_LISTENFORMESSAGESREQUEST']._serialized_end=591
  _globals['_RESPONSE']._serialized_start=593
  _globals['_RESPONSE']._serialized_end=636
  _globals['_CHATSERVICE']._serialized_start=639
  _globals['_CHATSERVICE']._serialized_end=1018
# @@protoc_insertion_point(module_scope)
