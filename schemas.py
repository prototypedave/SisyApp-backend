from extensions import ma
from marshmallow import fields, validate


class ClientSchema(ma.Schema):
    id = fields.Str(required=True, validate=validate.Length(min=7, max=9))
    first_name = fields.Str(required=True, validate=validate.Length(min=2, max=80))
    middle_name = fields.Str(allow_none=True)
    last_name = fields.Str(required=True, validate=validate.Length(min=2, max=80))
    gender = fields.Str(required=True, validate=validate.OneOf(["M", "F", "O"]))
    mobile = fields.Str(required=True)
    occupation = fields.Str(required=True)
    title = fields.Str(allow_none=True)
    salary = fields.Int(required=True)
    company = fields.Str(required=True)
    alias = fields.Str(allow_none=True)
    alias_mobile = fields.Str(allow_none=True)
    
    class Meta:
        ordered = True 
