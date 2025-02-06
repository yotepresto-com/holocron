from rest_framework import serializers


from .models import Config, Product, Person, NaturalPersonDetails, JuridicalPersonDetails, BlacklistPerson, \
    BlacklistNaturalPersonDetails, BlacklistJuridicalPersonDetails, BlacklistPersonAttribute, \
    BlacklistPersonAttributeValue, ProfileAttribute, Profile


class ConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = Config
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class NaturalPersonDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NaturalPersonDetails
        exclude = ['person', ]


class JuridicalPersonDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = JuridicalPersonDetails
        exclude = ['person', ]


class PersonSerializer(serializers.ModelSerializer):
    natural_person_details = NaturalPersonDetailsSerializer(required=False)
    juridical_person_details = JuridicalPersonDetailsSerializer(required=False)

    def validate(self, data):
        if data.get('type') == 'juridical' and 'juridical_person_details' not in data:
            raise serializers.ValidationError("juridical_person_details is required for juridical person")
        if data.get('type') == 'natural' and 'natural_person_details' not in data:
            raise serializers.ValidationError("natural_person_details is required for natural person")

        return super().validate(data)

    def create(self, validated_data):
        natural_person_details_data = None
        juridical_person_details_data = None

        if 'natural_person_details' in validated_data:
            natural_person_details_data = validated_data.pop('natural_person_details')
        elif 'juridical_person_details' in validated_data:
            juridical_person_details_data = validated_data.pop('juridical_person_details')

        person = Person.objects.create(**validated_data)

        if natural_person_details_data:
            NaturalPersonDetails.objects.create(person=person, **natural_person_details_data)
        elif juridical_person_details_data:
            JuridicalPersonDetails.objects.create(person=person, **juridical_person_details_data)

        return person

    class Meta:
        model = Person
        fields = '__all__'


class PersonAttributeSerializer(serializers.Serializer):
    name = serializers.CharField()
    value = serializers.CharField()


class BlacklistNaturalPersonDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlacklistNaturalPersonDetails
        exclude = ['blacklist_person', ]


class BlacklistJuridicalPersonDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlacklistJuridicalPersonDetails
        exclude = ['blacklist_person', ]


class BlacklistPersonSerializer(serializers.ModelSerializer):
    natural_person_details = BlacklistNaturalPersonDetailsSerializer(required=False)
    juridical_person_details = BlacklistJuridicalPersonDetailsSerializer(required=False)
    attributes = PersonAttributeSerializer(many=True, required=False)

    def validate(self, data):
        if data.get('type') == 'juridical' and 'juridical_person_details' not in data:
            raise serializers.ValidationError("juridical_person_details is required for juridical person")
        if data.get('type') == 'natural' and 'natural_person_details' not in data:
            raise serializers.ValidationError("natural_person_details is required for natural person")

        return super().validate(data)

    def create(self, validated_data):
        natural_person_details_data = None
        juridical_person_details_data = None

        if 'natural_person_details' in validated_data:
            natural_person_details_data = validated_data.pop('natural_person_details')
        elif 'juridical_person_details' in validated_data:
            juridical_person_details_data = validated_data.pop('juridical_person_details')

        attributes = validated_data.pop('attributes', [])
        person = BlacklistPerson.objects.create(**validated_data)

        if natural_person_details_data:
            BlacklistNaturalPersonDetails.objects.create(blacklist_person=person, **natural_person_details_data)
        elif juridical_person_details_data:
            BlacklistJuridicalPersonDetails.objects.create(blacklist_person=person, **juridical_person_details_data)

        for attribute in attributes:
            pa, _ = BlacklistPersonAttribute.objects.get_or_create(attribute_name=attribute['name'])
            BlacklistPersonAttributeValue.objects.create(blacklist_person=person, attribute=pa, value=attribute['value'])

        return person

    class Meta:
        model = BlacklistPerson
        fields = '__all__'


class ProfileAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileAttribute
        fields = [
            'id',
            'name',
            'description',
            'type',
            'accepted_values',
            'is_transactional',
        ]
        read_only_fields = ['id']

class ProfileSerializer(serializers.ModelSerializer):
    # Read-only nested attributes (will be returned in detail views)
    attributes = ProfileAttributeSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id',
            'name',
            'accept_natural_person',
            'accept_legal_person',
            'attributes',
        ]
        read_only_fields = ['id', 'attributes']
