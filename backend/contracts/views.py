from rest_framework import viewsets, generics

from .models import Contracts
from .serializers import ContractSerializer


class ContractsViewset(viewsets.ModelViewSet):
    serializer_class = ContractSerializer
    queryset = Contracts.objects.order_by('id')


