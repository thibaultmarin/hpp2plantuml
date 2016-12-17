template<typename T>
class Class03 {
public:
	Class03();
	~Class03();
private:
	Class01* _obj;
	Class01* _data;
	list<Class02> _obj_list;
	T* _typed_obj;
};
