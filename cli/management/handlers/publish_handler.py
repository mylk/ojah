from django.conf import settings


class PublishHandler:

    def run(self, queue_item, classification):
        queue_item.score = 1 if classification == 'pos' else 0
        queue_item.published = False
        if settings.AUTO_PUBLISH and classification == 'pos':
            queue_item.published = True
        queue_item.save()
