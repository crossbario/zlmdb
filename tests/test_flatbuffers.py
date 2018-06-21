import flatbuffers
from _gen.crossbarfx import User, Date, Tag, Rating

RESULT = {
    'objects': 0,
    'bytes': 0
}


def test():
    global RESULT

    builder = flatbuffers.Builder(0)

    name = builder.CreateString('Homer Simpson')
    authid = builder.CreateString('homer')
    email = builder.CreateString('homer.simpson@example.com')

    User.UserStartTagsVector(builder, 2)
    builder.PrependUOffsetTRelative(Tag.Tag.GEEK)
    builder.PrependUOffsetTRelative(Tag.Tag.VIP)
    tags = builder.EndVector(2)

    ratings = None
    if False:
        _ratings = {
            'dawn-of-the-dead': 6.9,
            'day-of-the-dead': 7.5,
            'land-of-the-dead': 8.9
        }

        _ratings_strings = {
        }
        for name in _ratings.keys():
            _name = builder.CreateString(name)
            _ratings_strings[_name] = name

        User.UserStartRatingsVector(builder, len(_ratings))
        l = []
        for _name, _rating in _ratings.items():
            Rating.RatingStart(builder)
            Rating.RatingAddName(builder, _ratings_strings[_name])
            Rating.RatingAddRating(builder, _rating)
            rating = Rating.RatingEnd(builder)
            l.append(rating)
        ratings = builder.EndVector(len(_ratings))

    User.UserStart(builder)

    User.UserAddName(builder, name)
    User.UserAddAuthid(builder, authid)
    User.UserAddEmail(builder, email)
    User.UserAddBirthday(builder, Date.CreateDate(builder, 1950, 12, 24))
    User.UserAddIsFriendly(builder, True)
    User.UserAddTags(builder, tags)

    if ratings:
        User.UserAddRatings(builder, ratings)

    user = User.UserEnd(builder)

    builder.Finish(user)

    buf = builder.Output()

    #data = bytes(buf)

    RESULT['objects'] += 1
    RESULT['bytes'] += len(buf)
#    RESULT['bytes'] += len(data)


import timeit

N = 1000
M = 100000

for i in range(N):
    secs = timeit.timeit(test, number=M)
    ops = round(float(M) / secs, 1)
    print('{} objects/sec'.format(ops))
    print(RESULT)
