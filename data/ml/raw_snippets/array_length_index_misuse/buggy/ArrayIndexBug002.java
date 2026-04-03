
public class ArrayIndexBug002 {
    public static void main(String[] args) {
        String[] names = { "A", "B", "C" };

        System.out.println(names[names.length]);
    }
}