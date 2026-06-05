import React from "react";
import { UserOutlined } from "@ant-design/icons";
import { Avatar, Button, Empty, List, Modal, Popconfirm, Progress, Space, Typography } from "antd";
import { getUserDisplayName } from "../../lib/userName";

export function CourseStudentsModal({
  open,
  selectedCourse,
  courseStudents,
  courseStudentsPending,
  removingStudent,
  onClose,
  onRemoveStudent,
}) {
  return (
    <Modal
      title={selectedCourse ? `Студенты курса: ${selectedCourse.title}` : "Студенты курса"}
      open={open}
      onCancel={onClose}
      footer={null}
      width={720}
    >
      {courseStudents.length === 0 && !courseStudentsPending ? (
        <Empty description="На этот курс пока никто не записался" />
      ) : (
        <List
          loading={courseStudentsPending}
          dataSource={courseStudents}
          renderItem={(enrollment) => (
            <List.Item
              actions={[
                <Popconfirm
                  key="remove"
                  title="Удалить студента с курса?"
                  description="Доступ к материалам курса будет отозван."
                  okText="Удалить"
                  cancelText="Отмена"
                  okButtonProps={{ danger: true, loading: removingStudent }}
                  onConfirm={() => onRemoveStudent(enrollment?.user?.id)}
                >
                  <Button danger size="small" disabled={!enrollment?.user?.id}>
                    Удалить с курса
                  </Button>
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                avatar={<Avatar src={enrollment.user.profile_photo_url} icon={<UserOutlined />} />}
                title={getUserDisplayName(enrollment.user)}
                description={
                  <Space direction="vertical" size={2}>
                    <Typography.Text type="secondary">{enrollment.user.email}</Typography.Text>
                    <Typography.Text type="secondary">
                      Записан: {new Date(enrollment.enrolled_at).toLocaleString("ru-RU")}
                    </Typography.Text>
                    <Progress
                      percent={enrollment.progress?.progress_percent || 0}
                      size="small"
                      status="active"
                      format={(percent) => `${percent}%`}
                    />
                    <Typography.Text type="secondary">
                      Материалы: {enrollment.progress?.viewed_contents || 0}/{enrollment.progress?.total_contents || 0},
                      задания: {enrollment.progress?.completed_assignments || 0}/{enrollment.progress?.total_assignments || 0},
                      тесты: {enrollment.progress?.completed_quizzes || 0}/{enrollment.progress?.total_quizzes || 0},
                      модули: {enrollment.progress?.completed_modules || 0}/{enrollment.progress?.total_modules || 0}
                    </Typography.Text>
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      )}
    </Modal>
  );
}


