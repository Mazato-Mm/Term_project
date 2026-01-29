import java.util.ArrayList;
public class CourseRegister {
    private ArrayList<Student> studentInClass = new ArrayList<>();;
    private String courseID;
    public CourseRegister(String courseID){
        this.courseID = courseID;
    }
    // ลงทะเบียน
    public boolean register(Student s){
        for (Student st : studentInClass){
            if (st.getID().equals(s.getID())){
                return false;
            }
        }
        studentInClass.add(s);
        return true;
    }
    // ถอน
    public boolean drop(String ID){
        for (int i = 0 ; i < studentInClass.size() ; i++){
            if (studentInClass.get(i).getID().equals(ID)){
                studentInClass.remove(i);
                return true;
            }
        }return false;
    }

    public void printReg(){
        System.out.println(courseID);
        for (Student st : studentInClass){
            System.out.println(st.getID()+" "+st.getName()+" ");
        }
        System.out.println("Total students in this course: "+studentInClass.size());

    }
}
