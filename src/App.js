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
  const [suggestionTrigger, setGetSuggestionTrigger] = useState({})

  const addListItem = (newItem) => {
    setListItems([...listItems, newItem]);
    removeSuggestion(newItem.product.identifier);
    if (!searchQuery)
        triggerGetSuggestion();
  }

  const removeListItem = (identifier) => {
    setListItems(listItems.filter(item => item.product.identifier !== identifier));
    triggerGetSuggestion();
  }

  const removeSuggestion = (identifier) => {
    setSuggestions(suggestions.filter(item => item.product.identifier !== identifier));
  }

  const triggerGetSuggestion = () => {
    setGetSuggestionTrigger({}) // Forces a requery
  }

  const clearSearchQuery = () => {
    setSearchQuery('');
  }

  useEffect(() => {
    axios.post('/api/suggestion',
               {basket: listItems.map(value => value.product.identifier),
                query: searchQuery})
         .then(response => {
            setSuggestions(response.data['data']);
            document.getElementById('suggestionsContainer').scrollIntoView(false);
         })
         .catch(error => setSuggestions([]));
  }, [searchQuery, suggestionTrigger]);

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
                                                                    onClick={(event) => removeListItem(item.product.identifier)}>
                                                              <Typography.Text type="secondary">
                                                                <CloseOutlined />
                                                              </Typography.Text>
                                                            </Button>]}>
                                         <Checkbox>
                                           {item.product.name}
                                         </Checkbox>
                                       </List.Item>)}
                  rowKey={item => item.product.identifier}
                  style={{flexGrow: 1}} />
            <Divider />
            <List id="suggestionsContainer"
                  dataSource={suggestions}
                  renderItem={item => (<List.Item>
                                         <Typography.Link italic
                                                          type="secondary"
                                                          title={item.product.name + ' ⟵ ' +
                                                                 (item.antecedent_items.length ?
                                                                   item.antecedent_items.map(product => product.name).join(', ') :
                                                                   'empty list') +
                                                                 ' (' +
                                                                 item.measure.lift.toLocaleString('en-US',
                                                                                                  {minimumFractionDigits: 2,
                                                                                                   maximumFractionDigits: 2}) +
                                                                 ' lift)'}
                                                          onClick={(event) => addListItem(item)}>
                                           {item.product.name}
                                         </Typography.Link>
                                       </List.Item>)}
                  rowKey={item => item.product.identifier} />
          </Typography.Paragraph>
        </div>
      </Layout.Content>
      <Layout.Footer>
        <Input.Search allowClear
                      style={{width: '100%'}}
                      value={searchQuery}
                      /*enterButton*/
                      onChange={(event) => setSearchQuery(event.target.value)}
                      /*onSearch={(event) => triggerGetSuggestion()}*/ />
      </Layout.Footer>
    </Layout>
  );
}

export default App;
