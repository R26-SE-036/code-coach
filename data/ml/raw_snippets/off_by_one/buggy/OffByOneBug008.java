public class OffByOneBug008 {
    public static void main(String[] args) {
        String[] colors = { "red", "blue", "green" };

        for (int i = 0; i <= colors.length; i++) {
            System.out.println(colors[i]);
        }
    }
}