import React from "react";
import { UserOutlined } from "@ant-design/icons";
import { Avatar, Button, Empty, List, Modal, Popconfirm, Space, Typography } from "antd";

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
                  onConfirm={() => onRemoveStudent(enrollment.user.id)}
                >
                  <Button danger size="small">
                    Удалить с курса
                  </Button>
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                avatar={<Avatar src={enrollment.user.profile_photo_url} icon={<UserOutlined />} />}
                title={enrollment.user.full_name || enrollment.user.email}
                description={
                  <Space direction="vertical" size={2}>
                    <Typography.Text type="secondary">{enrollment.user.email}</Typography.Text>
                    <Typography.Text type="secondary">
                      Записан: {new Date(enrollment.enrolled_at).toLocaleString("ru-RU")}
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
