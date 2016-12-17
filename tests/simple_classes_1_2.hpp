enum Enum01 { VALUE_0, VALUE_1, VALUE_2 };

class Class01 {
protected:
	int _protected_var;
	bool _ProtectedMethod(int param);
	static bool _StaticProtectedMethod(bool param);
	virtual bool _AbstractMethod(int param) = 0;
public:
	int public_var;
	bool PublicMethod(int param);
	static bool StaticPublicMethod(bool param);
	virtual bool AbstractPublicMethod(int param) = 0;
};

class Class02 : public Class01 {
public:
	bool AbstractPublicMethod(int param) override;
private:
	int _private_var;
	bool _PrivateMethod(int param);
	static bool _StaticPrivateMethod(bool param);
	bool _AbstractMethod(int param) override;
};
