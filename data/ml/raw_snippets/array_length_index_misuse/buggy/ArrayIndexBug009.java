
public class ArrayIndexBug009 {
    public static void main(String[] args) {
        boolean[] flags = { true, false, true };

        if (flags[flags.length]) {
            System.out.println("Last flag is true");
        }
    }
}