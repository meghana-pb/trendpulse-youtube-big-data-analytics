import React from 'react';
import { Card, Text, Metric, Flex, BadgeDelta } from '@tremor/react';

export default function KPICard({ title, metric, delta, deltaType = 'moderateIncrease', icon: Icon, suffix = '' }) {
  return (
    <Card className="decoration-blue-500 max-w-xs mx-auto md:max-w-none hover:shadow-lg transition-shadow bg-white ring-1 ring-slate-200">
      <Flex alignItems="start">
        <div className="truncate">
          <Text className="text-slate-500 font-medium flex items-center gap-2">
            {Icon && <Icon size={16} className="text-slate-400" />}
            {title}
          </Text>
          <Metric className="truncate font-bold text-slate-800 mt-2">
            {metric}{suffix}
          </Metric>
        </div>
        {delta && (
          <BadgeDelta deltaType={deltaType}>{delta}</BadgeDelta>
        )}
      </Flex>
    </Card>
  );
}
