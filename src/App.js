import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import {Button, Checkbox, Divider, Input, Layout, List, PageHeader, Typography} from 'antd';
import {CloseOutlined} from "@ant-design/icons";
import logo from './logo.svg';

function App() {
  const [listItems, setListItems] = useState(Array.from({length: 20}, (_, index) => {return {id: index, name: 'Item #' + (index + 1)}}));
  const [suggestions, setSuggestions] = useState(Array.from({length: 5}, (_, index) => {return {id: index + 20, name: 'Suggestion #' + (index + 1)}}));
  const [searchQuery, setSearchQuery] = useState("");

  const addListItem = (newItem) => {
    setListItems([...listItems.filter(item => item.id !== newItem.id), newItem]);
  }

  const removeListItem = (id) => {
    setListItems(listItems.filter(item => item.id !== id));
  }

  const removeSuggestion = (id) => {
    setSuggestions(suggestions.filter(item => item.id !== id));
  }

  useEffect(() => {
    axios.post('/api/suggestion',
               {basket: listItems.map(value => value.id),
                query: searchQuery})
         .then(response => {
            setSuggestions(response.data['data']);
            document.getElementById('suggestionsContainer').scrollIntoView(false);
         })
         .catch(error => setSuggestions([]));
  }, [searchQuery]);

  return (
    <Layout style={{height: '100vh'}}>
      <Layout.Content style={{display: 'flex', flexDirection: 'column'}}>
        <PageHeader avatar={{src: logo}}
                    copyable={false}
                    title="Shopping Assistant" />
        <div style={{display: 'flex', flexDirection: 'column', flexGrow: 1, overflow: 'auto'}}>
          <Typography.Paragraph style={{display: 'flex', flexDirection: 'column', flexGrow: 1}}>
            <List dataSource={listItems}
                  renderItem={item => (<List.Item actions={[<Button type="text"
                                                                    onClick={(event) => removeListItem(item.id)}>
                                                              <Typography.Text type="secondary">
                                                                <CloseOutlined />
                                                              </Typography.Text>
                                                            </Button>]}>
                                         <Checkbox>
                                           {item.name}
                                         </Checkbox>
                                       </List.Item>)}
                  rowKey={item => item.id}
                  style={{flexGrow: 1}} />
            <Divider />
            <List id="suggestionsContainer"
                  dataSource={suggestions}
                  renderItem={item => (<List.Item>
                                         <Typography.Link italic
                                                          type="secondary"
                                                          onClick={(event) => {
                                                            addListItem(item);
                                                            removeSuggestion(item.id);
                                                            setSearchQuery(new String(searchQuery));
                                                          }}>
                                           {item.name}
                                         </Typography.Link>
                                       </List.Item>)}
                  rowKey={item => item.id} />
          </Typography.Paragraph>
        </div>
      </Layout.Content>
      <Layout.Footer>
        <Input allowClear
               style={{width: '100%'}}
               value={searchQuery}
               onChange={(event) => setSearchQuery(event.target.value)} />
      </Layout.Footer>
    </Layout>
  );
}

export default App;
