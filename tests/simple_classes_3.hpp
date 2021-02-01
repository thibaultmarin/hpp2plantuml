template<typename T>
class Class03 {
public:
	Class03();
	~Class03();
	void Method(Interface::Class04& c4);
private:
	Class01* _obj;
	Class01* _data;
	list<Class02> _obj_list;
	T* _typed_obj;
};

namespace Interface {

	class Class04 {
	public:
		Class04();
		~Class04();
	private:
		bool _flag;
		Class01* _obj;
		T _var;
	};

	class Class04_derived : public Class04 {
	public:
		Class04_derived();
		~Class04_derived();
	private:
		int _var;
	};

	struct Struct {
		int a;
	};
};

// Anonymous union (issue #9)
union {
	struct {
		float x;
		float y;
		float z;
	};
	struct {
		float rho;
		float theta;
		float phi;
	};
	float vec[3];
};
