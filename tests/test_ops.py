def test_insert1(env):
    users = []

    user1 = User()
    user1.oid = 1
    user1.name = 'Homer Simpson'
    user1.authid = 'homer'
    user1.email = 'homer.simpson@example.com'
    user1.birthday = datetime.date(1950, 12, 24)
    user1.is_friendly = True
    user1.tags = ['relaxed', 'beerfan']
    users.append(user1)

    user2 = User()
    user2.oid = 2
    user2.name = 'Crocodile Dundee'
    user2.authid = 'crocoboss'
    user2.email = 'croco@example.com'
    user2.birthday = datetime.date(1960, 2, 4)
    user2.is_friendly = False
    user2.tags = ['red', 'yellow']
    user2.referred_by = user1.oid
    users.append(user2)

    user3 = User()
    user3.oid = 3
    user3.name = 'Foobar Space'
    user3.authid = 'foobar'
    user3.email = 'foobar@example.com'
    user3.birthday = datetime.date(1970, 5, 7)
    user3.is_friendly = True
    user3.tags = ['relaxed', 'beerfan']
    user3.referred_by = user1.oid
    users.append(user3)

    with Transaction(env, write=True) as txn:
        for user in users:
            _user = txn.users[user.oid]
            if not _user:
                txn.users[user.oid] = user
                #txn.users_by_authid[user.authid] = user.oid
                print('user stored', user)
            else:
                print('user loaded', _user)

def test_insert2(env):
    with Transaction(env, write=True) as txn:
        for i in range(100):
            user = User()
            user.oid = i + 10
            user.name = 'Test {}'.format(i)
            user.authid = 'test-{}'.format(i)
            user.email = '{}@example.com'.format(user.authid)
            for j in range(10):
                user.ratings['test-rating-{}'.format(j)] = random.random()

            _user = txn.users[user.oid]
            if not _user:
                txn.users[user.oid] = user
                #txn.users_by_authid[user.authid] = user.oid
                print('user stored', user, user.oid, user.authid)
            else:
                print('user loaded', _user, _user.oid, _user.authid)


def test_insert3(env):
    oid = 4

    with Transaction(env, write=True) as txn:
        user = txn.users[oid]
        if not user:
            user = User()
            user.oid = oid
            user.name = 'Foobar Space'
            user.authid = 'foobar'
            user.email = 'foobar@example.com'
            user.birthday = datetime.date(1970, 5, 7)
            user.is_friendly = True
            user.tags = ['relaxed', 'beerfan']
            user.referred_by = 1

            txn.users[oid] = user
            print('user stored', user)
        else:
            print('user loaded', user)


def test_by_auth(env):
    with Transaction(env) as txn:
        for i in range(100):
            authid = 'test-{}'.format(i)
            oid = txn.idx_users_by_authid[authid]
            if oid:
                user = txn.users[oid]
                print('success: user "{}" loaded by authid "{}"'.format(oid, authid))
            else:
                print('failure: user not found for authid "{}"'.format(authid))


def test_by_email(env):
    with Transaction(env) as txn:
        for i in range(100):
            email = 'test-{}@example.com'.format(i)
            oid = txn.idx_users_by_email[email]
            if oid:
                user = txn.users[oid]
                print('success: user "{}" loaded by email "{}"'.format(oid, email))
            else:
                print('failure: user not found for email "{}"'.format(email))


def test_truncate_index(env):
    with Transaction(env, write=True) as txn:
        rows = txn.users_by_authid.truncate()
        print('users_by_authid truncated: {} rows'.format(rows))
