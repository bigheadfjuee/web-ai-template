<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ApiError, type User, type UserCreate, createUser, deleteUser, listUsers, updateUser } from '../api/users'

const users = ref<User[]>([])
const errorMsg = ref<string | null>(null)
const createForm = ref<UserCreate>({ username: '', email: '' })
const createError = ref<string | null>(null)
const editingId = ref<string | null>(null)
const editForm = ref<{ username: string; email: string }>({ username: '', email: '' })
const editError = ref<string | null>(null)

async function fetchUsers() {
  try {
    users.value = await listUsers()
    errorMsg.value = null
  } catch {
    errorMsg.value = 'Failed to load users.'
  }
}

onMounted(fetchUsers)

async function handleCreate() {
  createError.value = null
  try {
    await createUser({ username: createForm.value.username, email: createForm.value.email })
    createForm.value = { username: '', email: '' }
    await fetchUsers()
  } catch (e) {
    createError.value = e instanceof ApiError ? e.message : 'Failed to create user.'
  }
}

function startEdit(user: User) {
  editingId.value = user.id
  editForm.value = { username: user.username, email: user.email }
  editError.value = null
}

function cancelEdit() {
  editingId.value = null
  editError.value = null
}

async function handleUpdate(id: string) {
  editError.value = null
  try {
    await updateUser(id, { username: editForm.value.username, email: editForm.value.email })
    editingId.value = null
    await fetchUsers()
  } catch (e) {
    editError.value = e instanceof ApiError ? e.message : 'Failed to update user.'
  }
}

async function handleDelete(id: string) {
  try {
    await deleteUser(id)
    await fetchUsers()
  } catch {
    errorMsg.value = 'Failed to delete user.'
  }
}
</script>

<template>
  <section class="users-view">
    <h2>User Management</h2>

    <form class="create-form" @submit.prevent="handleCreate">
      <input v-model="createForm.username" type="text" placeholder="Username" required />
      <input v-model="createForm.email" type="email" placeholder="Email" required />
      <button type="submit">Add User</button>
      <span v-if="createError" class="error">{{ createError }}</span>
    </form>

    <p v-if="errorMsg" class="error">{{ errorMsg }}</p>

    <p v-if="users.length === 0 && !errorMsg" class="empty">No users yet.</p>

    <table v-else-if="users.length > 0">
      <thead>
        <tr>
          <th>Username</th>
          <th>Email</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <template v-if="editingId === user.id">
            <td><input v-model="editForm.username" type="text" required /></td>
            <td><input v-model="editForm.email" type="email" required /></td>
            <td>
              <button @click="handleUpdate(user.id)">Save</button>
              <button @click="cancelEdit">Cancel</button>
              <span v-if="editError" class="error">{{ editError }}</span>
            </td>
          </template>
          <template v-else>
            <td>{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>
              <button @click="startEdit(user)">Edit</button>
              <button class="delete" @click="handleDelete(user.id)">Delete</button>
            </td>
          </template>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<style scoped>
.users-view {
  margin-top: 1.5rem;
}
.create-form {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
  align-items: center;
}
input[type='text'],
input[type='email'] {
  padding: 0.35rem 0.6rem;
  border: 1px solid #d0d4dc;
  border-radius: 0.3rem;
  font-size: 0.9rem;
}
button {
  padding: 0.35rem 0.8rem;
  border: 1px solid #bbb;
  border-radius: 0.3rem;
  background: #f0f2f5;
  cursor: pointer;
  font-size: 0.9rem;
}
button.delete {
  background: #fdecea;
  border-color: #e57373;
  color: #b71c1c;
}
table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 0.5rem;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
th,
td {
  text-align: left;
  padding: 0.6rem 1rem;
  border-bottom: 1px solid #e8eaed;
  font-size: 0.9rem;
}
th {
  background: #f6f7f9;
  font-weight: 600;
}
.error {
  color: #c62828;
  font-size: 0.85rem;
}
.empty {
  color: #888;
  font-style: italic;
}
</style>
