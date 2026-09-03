
public class VivaDemo {
    public static void main(String[] args) {
        int[] marks = {70, 55, 88, 92};

        int total = 0;

        for (int i = 0; i < marks.length; i++ ){
            total = total + marks[i];
        }

        System.out.println("Total: " + total);
    }
}
