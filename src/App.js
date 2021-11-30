import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import {Button, Checkbox, Divider, Input, Layout, List, PageHeader, Typography} from 'antd';
import {CloseOutlined} from "@ant-design/icons";
import logo from './logo.svg';

function App() {
  const [listItems, setListItems] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");

  const addListItem = (newItem) => {
    setListItems([...listItems.filter(item => item.product.id !== newItem.product.id), newItem]);
  }

  const removeListItem = (id) => {
    setListItems(listItems.filter(item => item.product.id !== id));
    setSearchQuery(new String(searchQuery)); // Forces a requery
  }

  const removeSuggestion = (id) => {
    setSuggestions(suggestions.filter(item => item.product.id !== id));
  }

  useEffect(() => {
    axios.post('/api/suggestion',
               {basket: listItems.map(value => value.product.id),
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
                                                                    onClick={(event) => removeListItem(item.product.id)}>
                                                              <Typography.Text type="secondary">
                                                                <CloseOutlined />
                                                              </Typography.Text>
                                                            </Button>]}>
                                         <Checkbox>
                                           {item.product.name}
                                         </Checkbox>
                                       </List.Item>)}
                  rowKey={item => item.product.id}
                  style={{flexGrow: 1}} />
            <Divider />
            <List id="suggestionsContainer"
                  dataSource={suggestions}
                  renderItem={item => (<List.Item>
                                         <Typography.Link italic
                                                          type="secondary"
                                                          title={item.product.name + ' (predicted from ' +
                                                                 (item.base.length ?
                                                                   item.base.map(product => product.name).join(', ') :
                                                                   'empty list') +
                                                                 ' with lift of ' +
                                                                 item.lift.toLocaleString('en-US',
                                                                                          {minimumFractionDigits: 2,
                                                                                           maximumFractionDigits: 2}) +
                                                                 ')'}
                                                          onClick={(event) => {
                                                            addListItem(item);
                                                            removeSuggestion(item.product.id);
                                                            setSearchQuery(new String(searchQuery)); // Forces a requery
                                                          }}>
                                           {item.product.name}
                                         </Typography.Link>
                                       </List.Item>)}
                  rowKey={item => item.product.id} />
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
