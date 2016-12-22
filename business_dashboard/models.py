from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Way(models.Model):
    waypoints = models.ManyToManyField('Waypoint', related_name='test', through='WaypointOrder')
    speed_limit = models.CharField(max_length=200)
    def __str__(self):
        return 'num waypoints: %s, speed limit: %s' % (self.waypoints.count(), self.speed_limit)

    def __repr__(self):
        return 'speed limit: %s' % self.speed_limit

class Waypoint(models.Model):
    osm_id = models.IntegerField(default='0')
    lat = models.FloatField()
    lng = models.FloatField()
    ways = models.ManyToManyField(Way)
    def __str__(self):
        return '(%s, %s)' % (self.lat, self.lng)

    def __repr__(self):
        return '(%s, %s)' % (self.lat, self.lng)

class Business(models.Model):
    loc = models.ForeignKey(Waypoint, related_name='+')
    street_loc = models.ForeignKey(Waypoint, related_name='+')
    name = models.CharField(max_length=200)
    speed_limit = models.CharField(max_length=200)

class WaypointOrder(models.Model):
    number = models.PositiveIntegerField()
    way = models.ForeignKey(Way)
    waypoint = models.ForeignKey(Waypoint)
