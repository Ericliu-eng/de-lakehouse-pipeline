from tests.test_sql_queries import split_sql_statements


#Verify that split_sql_statements correctly splits a SQL 
#string into individual statements using the semicolon (;) delimiter.
#unit test 1
def test_split_sql_statements_basic() -> None:
    sql_input = "SELECT 1;    SELECT 2; "
    sqls = split_sql_statements(sql_input)
    assert sqls == ["SELECT 1", "SELECT 2"]

#Ensure that split_sql_statements ignores empty SQL fragments caused by consecutive semicolons or trailing semicolons.
#unti test 2
def test_split_sql_statements_removes_empty() -> None:
    sql_input = ";; SELECT 1;; ;\n"
    sqls = split_sql_statements(sql_input)
    assert sqls == ["SELECT 1"]


#unti test 3
def test_split_sql_statements_strips_whitespace() ->None:
    sql_input = "  SELECT 1 ; \n   SELECT 2   ;"
    sqls = split_sql_statements(sql_input)
    assert sqls == ["SELECT 1","SELECT 2"]
#Edge case
def test_split_sql_statements_empty_or_whitespace_input() ->None:
    assert split_sql_statements("") == []
    assert split_sql_statements("   \n\t") == []