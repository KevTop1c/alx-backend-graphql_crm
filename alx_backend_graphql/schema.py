"""Imports for GraphQL"""

import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

# pylint: disable=unnecessary-pass
class Query(CRMQuery, graphene.ObjectType):
    """
    Root Query combining all app-level queries.
    Currently includes CRM queries for customers, products, and orders.
    """
    pass


class Mutation(CRMMutation, graphene.ObjectType):
    """
    Root Mutation combining all app-level mutations.
    Currently includes CRM mutations for creating customers, products, and orders.
    """
    pass


# Create the schema with both query and mutation support
schema = graphene.Schema(query=Query, mutation=Mutation)
