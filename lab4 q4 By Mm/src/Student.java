public class Student {
    private String id, name, major;
    public Student(){
        this.id = "";
        this.name = "";
        this.major = "";
    }
    public Student(String id, String name, String major){
        this.id = id;
        this.name = name;
        this.major = major;
    }
    public void setID(String id){
        this.id = id;
    }
    public void setName(String name){
        this.name = name;
    }
    public void setMajor(String major){
        this.major = major;
    }
    public String getID(){
        return this.id;
    }
    public String getName(){
        return this.name;
    }
    public String getMajor(){
        return this.major;
    }
    public int getDigit(int start, int end){
        return Integer.parseInt(this.id.substring(start, end+1));
    }
    public int getFacultyCode(){
        return getDigit(8,9);
    }
    public int getLevelCode(){
        return getDigit(2,2);
    }
    public int getYear(){
        return getDigit(0,1);
    }
    public boolean sameYear(Student other){
        return (this.getYear() == other.getYear());
    }
    public boolean sameLevel(Student other){
        return (this.getLevelCode() == other.getLevelCode());
    }
    public boolean sameFaculty(Student other){
        return (this.getFacultyCode() == other.getFacultyCode());
    }
}