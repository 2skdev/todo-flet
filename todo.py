import colorsys
import datetime
import os
import random
import re
import uuid

import flet as ft
from flet.padding import symmetric

md = os.path.dirname(__file__) + '/todo.md'

class ToDo:
  REGEXP = re.compile(r'- \[(?P<done> |x)\] ((?P<due>[0-9|\-]{10}) )?((\+(?P<prj>\w+)) )?(?P<content>.+)')
  
  def __init__(self, **args):
    self.__dict__.update(**args)

  @classmethod
  def from_string(cls, str):
    m = cls.REGEXP.search(str)
    if m:
      return cls(
        done=m.group('done') == 'x',
        due=datetime.datetime.strptime(m.group('due'), '%Y-%m-%d').date() if m.group('due') else None,
        prj=m.group('prj'),
        content=m.group('content')
      )
    else:
      return None

  def __str__(self):
    arr = [
      '[%s]' % ('x' if self.done else ' '),
      self.due.strftime('%Y-%m-%d') if self.due else None,
      '+%s' % self.prj if self.prj else None,
      self.content
    ]

    return '- ' + ' '.join([x for x in arr if x])


class Task(ft.UserControl):
  def __init__(self, key, todo, on_update, on_delete):
    super().__init__()
    self.key = key
    self.todo = todo
    self.on_update = on_update
    self.on_delete = on_delete
    self.__edit_mode = False

  @property
  def edit_mode(self):
    return self.__edit_mode
  
  @edit_mode.setter
  def edit_mode(self, value):
    self.__edit_mode = value
    self.ref_content.current.visible = not value
    self.ref_prj.current.visible = not value and self.todo.prj is not None
    self.ref_input.current.visible = value

  def build(self):
    self.ref_content = ft.Ref[ft.Text]()
    self.ref_prj = ft.Ref[ft.Container]()
    self.ref_input = ft.Ref[ft.TextField]()
    self.ref_delete = ft.Ref[ft.IconButton]()

    return ft.Column(
      controls=[
        ft.Row(
          controls=[
            ft.Checkbox(
              value=self.todo.done,
              on_change=self.check
            ),
            ft.Container(
              expand=1,
              on_click=self.edit,
              on_hover=self.hover,
              content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                height=40,
                controls=[
                  ft.Row(
                    controls=[
                      ft.Container(
                        ref=self.ref_prj,
                        visible=self.todo.prj is not None,
                        content=ft.Text(
                          value=self.todo.prj
                        ),
                        bgcolor=prj_colors[self.todo.prj],
                        border_radius=20,
                        padding=symmetric(vertical=5, horizontal=10),
                      ),
                      ft.Text(
                        ref=self.ref_content,
                        value=self.todo.content,
                      ),
                    ]
                  ),
                  ft.TextField(
                    ref=self.ref_input,
                    visible=False,
                    expand=1,
                    on_submit=self.submit,
                    on_blur=self.cancel,
                  ),
                  ft.IconButton(
                    ref=self.ref_delete,
                    icon=ft.icons.DELETE,
                    visible=False,
                    on_click=self.delete,
                  )
                ],
              ),
            ),
          ]
        ),
      ]
    )

  def delete(self, e):
    self.on_delete(self.key)

  def hover(self, e):
    self.ref_delete.current.visible = e.data == 'true'
    self.update()

  def check(self, e):
    self.on_update(self.key, {'done': e.data == 'true'})
  
  def edit(self, e):
    self.ref_input.current.value = str(self.todo)[6:];
    self.ref_input.current.focus()
    self.edit_mode = True
    self.update()

  def submit(self, e):
    new_todo = ToDo.from_string(str(self.todo)[:6] + self.ref_input.current.value)

    self.ref_content.current.value = new_todo.content;
    self.ref_prj.current.value = new_todo.prj
    self.ref_prj.current.value = prj_colors[self.todo.prj]

    self.edit_mode = False
    self.update()

    self.on_update(self.key, new_todo.__dict__)

  def cancel(self, e):
    self.edit_mode = False
    self.update()

prj_colors = {}
def generate_color(hue):
  r, g, b = colorsys.hsv_to_rgb(hue, 0.7, 0.7)
  return '#%02x%02x%02x' % (int(r*255), int(g*255), int(b*255))
def add_prg_color(prj):
  if prj not in prj_colors:
    prj_colors[prj] = generate_color(len(prj_colors) / 32)

todos = {}
with open(md, 'r') as f:
  for l in f:
    todo = ToDo.from_string(l)
    if todo:
      todos[uuid.uuid4()] = todo
    
    add_prg_color(todo.prj)


def main(page: ft.Page):
  def on_update(key, data):
    todos[key].__dict__.update(data)
    with open(md, 'w') as f:
      for todo in todos.values():
        f.write(str(todo) + '\n')

    add_prg_color(odos[key].todo)
    page.controls = create_todo_list()
    page.update()

  def on_delete(key):
    del todos[key]
    print(todos)
    with open(md, 'w') as f:
      for todo in todos.values():
        f.write(str(todo) + '\n')
    page.controls = create_todo_list()
    page.update()

  def create_todo_list():
    today = datetime.date.today()
    maxdate = datetime.datetime.max.date()

    page.controls = []
    for item in sorted(todos.items(), key=lambda item: item[1].due if item[1].due else maxdate):
      print(item[1].__dict__)
      page.controls.append(Task(*item, on_update=on_update, on_delete=on_delete))

    page.update()

  page.window_frameless = True
  page.window_opacity = 0.9
  page.scroll = ft.ScrollMode.AUTO
  create_todo_list()

ft.app(target=main, port=5000)