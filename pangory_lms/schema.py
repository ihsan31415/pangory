import graphene

import accounts.schema
import courses.schema
import discussions.schema
import exams.schema
import certificates.schema

class Query(
    accounts.schema.Query,
    courses.schema.Query,
    discussions.schema.Query,
    exams.schema.Query,
    certificates.schema.Query,
    graphene.ObjectType
):
    pass

class Mutation(
    accounts.schema.Mutation,
    courses.schema.Mutation,
    discussions.schema.Mutation,
    exams.schema.Mutation,
    certificates.schema.Mutation,
    graphene.ObjectType
):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation) 