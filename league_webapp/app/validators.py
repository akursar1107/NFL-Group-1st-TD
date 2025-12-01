"""
Marshmallow schemas for API input validation
"""
from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class PickCreateSchema(Schema):
    """Validation schema for creating a new pick"""
    user_id = fields.Integer(required=True, validate=validate.Range(min=1))
    game_id = fields.Integer(required=True, validate=validate.Range(min=1))
    pick_type = fields.String(
        required=True,
        validate=validate.OneOf(['FTD', 'ATTS'])
    )
    player_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100)
    )
    player_position = fields.String(
        validate=validate.OneOf(['QB', 'RB', 'WR', 'TE', 'UNK']),
        load_default='UNK'
    )
    odds = fields.Integer(
        required=True,
        validate=validate.Range(min=-10000, max=10000)
    )
    stake = fields.Float(
        validate=validate.Range(min=0.01, max=1000.0),
        load_default=1.0
    )

    @validates_schema
    def validate_player_name_not_empty(self, data, **kwargs):
        """Ensure player name is not just whitespace"""
        if 'player_name' in data and not data['player_name'].strip():
            raise ValidationError('Player name cannot be empty or whitespace', 'player_name')


class PickUpdateSchema(Schema):
    """Validation schema for updating an existing pick"""
    player_name = fields.String(validate=validate.Length(min=1, max=100))
    player_position = fields.String(
        validate=validate.OneOf(['QB', 'RB', 'WR', 'TE', 'UNK'])
    )
    pick_type = fields.String(
        validate=validate.OneOf(['FTD', 'ATTS'])
    )
    odds = fields.Integer(validate=validate.Range(min=-10000, max=10000))
    stake = fields.Float(validate=validate.Range(min=0.01, max=1000.0))

    @validates_schema
    def validate_player_name_not_empty(self, data, **kwargs):
        """Ensure player name is not just whitespace"""
        if 'player_name' in data and not data['player_name'].strip():
            raise ValidationError('Player name cannot be empty or whitespace', 'player_name')


class GradeWeekSchema(Schema):
    """Validation schema for grading a week"""
    week = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=22)
    )
    season = fields.Integer(
        validate=validate.Range(min=2020, max=2030),
        load_default=2025
    )


class ImportDataSchema(Schema):
    """Validation schema for data import"""
    season = fields.Integer(
        validate=validate.Range(min=2020, max=2030),
        load_default=2025
    )
