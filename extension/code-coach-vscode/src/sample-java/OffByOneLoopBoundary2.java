public class OffByOneLoopBoundary2 {
    public static void main(String[] args) {
        String[] students = { "Alice", "Bob", "Charlie", "Diana" };
        for (int i = 0; i <= students.length; i++) {
            System.out.println("Student: " + students[i]);
        }
    }
}
