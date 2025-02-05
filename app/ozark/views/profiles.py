from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Profile, Attribute
from .serializers import ProfileSerializer, AttributeSerializer


class ProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet to handle all Profile CRUD operations plus nested attribute endpoints.

    Endpoints:
      - POST   /profiles                  -> create()
      - GET    /profiles                  -> list()
      - GET    /profiles/{id}            -> retrieve()
      - PATCH  /profiles/{id}            -> partial_update()
      - DELETE /profiles/{id}            -> destroy()
      - POST   /profiles/{id}/attribute  -> create_attribute()
      - DELETE /profiles/{id}/attribute/{attribute_id} -> delete_attribute()
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    # -------------------------------------------------------------------------
    # 5.5. Create an Attribute in a Profile
    #    POST /profiles/{id}/attribute
    # -------------------------------------------------------------------------
    @action(detail=True, methods=['post'], url_path='attribute')
    def create_attribute(self, request, pk=None):
        """Adds a new attribute definition to an existing profile."""
        profile = self.get_object()
        serializer = AttributeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(profile=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # 5.6. Delete an Attribute from a Profile
    #   DELETE /profiles/{id}/attribute/{attribute_id}
    # -------------------------------------------------------------------------
    @action(detail=True, methods=['delete'], url_path=r'attribute/(?P<attribute_id>[^/.]+)')
    def delete_attribute(self, request, pk=None, attribute_id=None):
        """Permanently removes a specific attribute from a profile."""
        profile = self.get_object()
        try:
            attribute = profile.attributes.get(id=attribute_id)
        except Attribute.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        attribute.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Note: The usual create, list, retrieve, partial_update, and destroy
    #       actions are already inherited from ModelViewSet.
