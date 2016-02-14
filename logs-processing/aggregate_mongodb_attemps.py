# None of those worked...

.runCommand(
   { aggregate: "users.clicks",
     pipeline: [
                 { $project: { tags: 1 } },
                 { $unwind: "$tags" },
                 { $group: {
                             _id: "$tags",
                             count: { $sum : 1 }
                           }
                 }
               ]
   }
)

a.users.clicks.aggregate([{'$group' : {'uid' : 66, 'total': {'$sum' : 'n'}}}])

a.users.clicks.aggregate([ { 
    '$group': { 
        '_id': 66, 
        'total': { 
            '$sum': "$wins" 
        } 
    } 
} ] )

a.users.clicks.aggregate([{'$project': {'blorg': {'uid': 66}}}, { 
    '$group': { 
        '_id': {'uid': '$blorg'}, 
        'total': { 
            '$sum': 1 
        } 
    } 
} ] )
