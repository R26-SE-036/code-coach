
public class ArrayIndexBug006 {
    public static void main(String[] args) {
        String[] letters = { "A", "B", "C", "D" };

        System.out.println(letters[letters.length]);
    }
}