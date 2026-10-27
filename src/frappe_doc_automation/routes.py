from .render import slug


def discover_routes(catalogue, limit=100):
    routes = [{'name': 'desk', 'path': '/app'}]
    for app in catalogue['apps']:
        for doc in app['doctypes']:
            if not doc['istable']:
                routes.append({'name': slug(app['name'] + '-' + doc['name']), 'path': '/app/' + slug(doc['name']), 'doctype': doc['name']})
        for report in app['reports']:
            routes.append({'name': 'report-' + slug(report['name']), 'path': '/app/query-report/' + slug(report['name'])})
    return routes[:limit]
