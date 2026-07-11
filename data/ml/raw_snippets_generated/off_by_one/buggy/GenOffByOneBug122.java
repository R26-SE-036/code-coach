public class GenOffByOneBug122 {
    static void show(int[] values) {
        for (int i = 0; i <= values.length; i++) {
            System.out.println(values[i]);
        }
    }
}
