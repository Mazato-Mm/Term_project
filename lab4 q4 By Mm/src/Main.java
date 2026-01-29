import java.util.ArrayList;
import java.util.Scanner;
public class Main{
    public static void main(String[] args){
        String name;
        CourseRegister course = new CourseRegister("2301260");
        Scanner sc = new Scanner(System.in);
        System.out.println("Enter ID, name, major ");
        while(true){
            ArrayList<String> st = new ArrayList<>();
            String data[] = sc.nextLine().split(" ");
            if(data[0].equals("x") || data[0].equals('X'))
                break;
            Student student = new Student(data[0],data[1]+" "+data[2],data[3]);
            course.register(student);
            System.out.println(data[1]+" REGISTERED SUCCESSFULLY");
        }
        course.printReg();
        System.out.println("Drop student -> Enter ID of the student: ");
        String drop = sc.next();
        course.drop(drop);
        course.printReg();
    }
}