import React from 'react';
import { useScheduleData } from './hooks/useScheduleData';
import { ScheduleForm } from './components/ScheduleForm';
import { ScheduleList } from './components/ScheduleList';

import { DuplicateWarningModal } from './components/DuplicateWarningModal';

export default function UploadSchedule() {
  const scheduleHook = useScheduleData();

  return (
    <div className="space-y-6">
      <ScheduleForm hook={scheduleHook} />
      <ScheduleList hook={scheduleHook} />
      <DuplicateWarningModal
        isOpen={scheduleHook.showDuplicateModal}
        onClose={scheduleHook.handleCloseDuplicateModal}
        onConfirm={scheduleHook.handleConfirmDuplicateSubmit}
        duplicates={scheduleHook.duplicateWarnings}
      />
    </div>
  );
}
