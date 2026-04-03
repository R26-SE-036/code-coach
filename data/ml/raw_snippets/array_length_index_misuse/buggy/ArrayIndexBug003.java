
public class ArrayIndexBug003 {
    public static void main(String[] args) {
        int[] values = { 7, 8, 9, 10 };
        int index = values.length;

        System.out.println(values[index]);
    }
}