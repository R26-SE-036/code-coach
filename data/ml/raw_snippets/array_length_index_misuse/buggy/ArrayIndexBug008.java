
public class ArrayIndexBug008 {
    public static void main(String[] args) {
        char[] letters = { 'A', 'B', 'C' };
        int index = letters.length;

        System.out.println(letters[index]);
    }
}
