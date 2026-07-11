public class GenWhileNoUpdateBug108 {
    static void pump(boolean active, int total) {
        while (!active) {
            System.out.println(total);
            total++;
        }
    }
}
